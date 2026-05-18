#ifndef BOARD_HAS_PSRAM
#error "Enable OPI PSRAM for LilyGo T5-ePaper-S3."
#endif

#include <Arduino.h>
#include "epd_driver.h"
#define _GFXFONT_H_
#include <Adafruit_GFX.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <U8g2_for_Adafruit_GFX.h>
#include <WiFi.h>
#include <Wire.h>
#include <time.h>
#include "utilities.h"
#include <TouchDrvGT911.hpp>

#if __has_include("config_private.h")
#include "config_private.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID ""
#endif

#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD ""
#endif

#ifndef STATE_URL
#define STATE_URL "http://192.168.1.2:8765/state.json"
#endif

#ifndef NTP_TIMEZONE_OFFSET
#define NTP_TIMEZONE_OFFSET (8 * 3600)  // UTC+8; override in config_private.h
#endif

namespace {

constexpr uint8_t BLACK = 0;
constexpr uint8_t DARK_GRAY = 80;
constexpr uint8_t LIGHT_GRAY = 210;
constexpr uint8_t WHITE = 255;
constexpr uint32_t REFRESH_INTERVAL_MS = 60000;
constexpr uint32_t WIFI_TIMEOUT_MS = 20000;

// Header touch zone X boundaries
constexpr int32_t ZONE_BRAND_X  = 195;  // brand | agent-0
constexpr int32_t ZONE_AGENT0_X = 500;  // agent-0 | agent-1
constexpr int32_t ZONE_AGENT1_X = 770;  // agent-1 | clock
constexpr int32_t HEADER_BOTTOM = 82;

uint8_t *framebuffer = nullptr;
uint32_t last_refresh_ms = 0;
bool touch_active = false;
uint8_t text_scale = 1;
int16_t text_scale_origin_x = 0;
int16_t text_scale_origin_y = 0;

enum ViewMode { OVERVIEW, AGENT0_FULL, AGENT1_FULL };
ViewMode current_mode = OVERVIEW;

struct DisplayView;          // forward
DisplayView *current_view_ptr = nullptr;
bool view_valid = false;

TouchDrvGT911 touch_ctrl;

class EpdFramebufferCanvas : public Adafruit_GFX {
 public:
  EpdFramebufferCanvas() : Adafruit_GFX(EPD_WIDTH, EPD_HEIGHT) {}

  void drawPixel(int16_t x, int16_t y, uint16_t color) override {
    if (!framebuffer || x < 0 || y < 0 || x >= EPD_WIDTH || y >= EPD_HEIGHT) {
      return;
    }
    const uint8_t ink = color ? BLACK : WHITE;
    if (text_scale <= 1) {
      epd_draw_pixel(x, y, ink, framebuffer);
      return;
    }

    const int16_t sx = text_scale_origin_x + (x - text_scale_origin_x) * text_scale;
    const int16_t sy = text_scale_origin_y + (y - text_scale_origin_y) * text_scale;
    for (uint8_t dx = 0; dx < text_scale; ++dx) {
      for (uint8_t dy = 0; dy < text_scale; ++dy) {
        const int16_t px = sx + dx;
        const int16_t py = sy + dy;
        if (px >= 0 && py >= 0 && px < EPD_WIDTH && py < EPD_HEIGHT) {
          epd_draw_pixel(px, py, ink, framebuffer);
        }
      }
    }
  }
};

EpdFramebufferCanvas canvas;
U8G2_FOR_ADAFRUIT_GFX u8g2;

struct QuotaView {
  String label;
  float remaining = 0;
  float limit = 0;
  int percent = 0;
  String reset;
};

struct TaskView {
  String name = "等待任务";
  String status = "idle";
};

struct AgentView {
  String label = "Agent";
  TaskView tasks[5];
  size_t task_count = 0;
  size_t task_total_count = 0;
  QuotaView quotas[2];
  size_t quota_count = 0;
};

struct DisplayView {
  String task_name = "Waiting for task";
  String status = "idle";
  String status_label = "Idle";
  String detail = "State not loaded";
  int progress = 0;
  String updated_at;
  TaskView tasks[3];
  size_t task_count = 0;
  size_t task_total_count = 0;
  QuotaView quotas[2];
  size_t quota_count = 0;
  AgentView agents[2];
  size_t agent_count = 0;
};

DisplayView g_view;

void clearFramebuffer() {
  memset(framebuffer, 0xFF, EPD_WIDTH * EPD_HEIGHT / 2);
}

void setFontLarge() {
  u8g2.setFont(u8g2_font_wqy16_t_gb2312);
}

void setFontBody() {
  u8g2.setFont(u8g2_font_wqy14_t_gb2312);
}

void setFontSmall() {
  u8g2.setFont(u8g2_font_wqy14_t_gb2312);
}

void textAt(const String &text, int32_t x, int32_t y) {
  text_scale = 1;
  text_scale_origin_x = x;
  text_scale_origin_y = y;
  u8g2.setCursor(x, y);
  u8g2.print(text);
}

void textAt2x(const String &text, int32_t x, int32_t y) {
  text_scale = 2;
  text_scale_origin_x = x;
  text_scale_origin_y = y;
  u8g2.setCursor(x, y);
  u8g2.print(text);
  text_scale = 1;
}

void textAtBold(const String &text, int32_t x, int32_t y, bool large = false) {
  if (large) {
    textAt2x(text, x, y);
    textAt2x(text, x + 1, y);
    return;
  }
  textAt(text, x, y);
  textAt(text, x + 1, y);
}

// Right-align: text ends at right_x. Font must be set before calling.
void textAtRight(const String &text, int32_t right_x, int32_t y,
                 bool bold = false, bool large = false) {
  int tw = u8g2.getUTF8Width(text.c_str());
  if (large) tw *= 2;
  const int32_t x = right_x - tw;
  if (large) {
    textAt2x(text, x, y);
    if (bold) textAt2x(text, x + 1, y);
  } else {
    textAt(text, x, y);
    if (bold) textAt(text, x + 1, y);
  }
}

void rect(int32_t x, int32_t y, int32_t w, int32_t h, uint8_t color) {
  epd_draw_rect(x, y, w, h, color, framebuffer);
}

void fill(int32_t x, int32_t y, int32_t w, int32_t h, uint8_t color) {
  epd_fill_rect(x, y, w, h, color, framebuffer);
}

void line(int32_t x0, int32_t y0, int32_t x1, int32_t y1, uint8_t color = BLACK) {
  epd_draw_line(x0, y0, x1, y1, color, framebuffer);
}

String ellipsize(const String &value, size_t max_len) {
  if (value.length() <= max_len) {
    return value;
  }
  if (max_len <= 3) {
    return value.substring(0, max_len);
  }
  return value.substring(0, max_len - 3) + "...";
}

String ellipsizeUtf8(const String &value, size_t max_chars) {
  size_t chars = 0;
  size_t end = 0;
  for (size_t i = 0; i < value.length();) {
    if (chars >= max_chars) {
      return value.substring(0, end) + "...";
    }

    const uint8_t c = static_cast<uint8_t>(value[i]);
    size_t step = 1;
    if ((c & 0x80) == 0) {
      step = 1;
    } else if ((c & 0xE0) == 0xC0) {
      step = 2;
    } else if ((c & 0xF0) == 0xE0) {
      step = 3;
    } else if ((c & 0xF8) == 0xF0) {
      step = 4;
    }

    if (i + step > value.length()) {
      break;
    }
    i += step;
    end = i;
    chars++;
  }
  return value;
}

String taskStatusShort(const String &status) {
  if (status == "running" || status == "thinking") {
    return "进行";
  }
  if (status == "needs_action") {
    return "待处理";
  }
  if (status == "done") {
    return "完成";
  }
  if (status == "failed") {
    return "失败";
  }
  return "空闲";
}

String englishStatus(const String &status) {
  if (status == "thinking")     return "Thinking";
  if (status == "needs_action") return "Needs action";
  if (status == "running")      return "Running";
  if (status == "done")         return "Done";
  if (status == "failed")       return "Failed";
  return "Idle";
}

String displayStatus(const DisplayView &view) {
  if (view.status_label.length()) return view.status_label;
  if (view.status == "thinking")     return "思考中";
  if (view.status == "needs_action") return "待处理";
  if (view.status == "running")      return "运行中";
  if (view.status == "done")         return "已完成";
  if (view.status == "failed")       return "失败";
  return "空闲";
}

void syncNTP() {
  configTime(NTP_TIMEZONE_OFFSET, 0, "pool.ntp.org", "ntp.aliyun.com");
  struct tm t;
  const uint32_t start = millis();
  while (!getLocalTime(&t, 100) && millis() - start < 5000) {}
  Serial.println(getLocalTime(&t, 0) ? "NTP synced" : "NTP sync timeout");
}

String clockString() {
  struct tm t;
  if (!getLocalTime(&t, 0)) return "--:--";
  char buf[6];
  strftime(buf, sizeof(buf), "%H:%M", &t);
  return String(buf);
}

void drawBar(int32_t x, int32_t y, int32_t w, int32_t h, int percent) {
  percent = constrain(percent, 0, 100);
  rect(x, y, w, h, BLACK);
  if (percent > 0) {
    fill(x + 2, y + 2, ((w - 4) * percent) / 100, h - 4, BLACK);
  }
}

// Draw a filled (active) or outline (idle) status dot
void drawStatusDot(int32_t cx, int32_t cy, bool active) {
  if (active) {
    canvas.fillCircle(cx, cy, 7, 0);
  } else {
    canvas.drawCircle(cx, cy, 7, 0);
  }
}

// Draw the 4-zone header bar
void drawHeader(const DisplayView &view, ViewMode mode) {
  constexpr int32_t safe_x = 20;

  // Vertical zone dividers (top border → header line)
  line(ZONE_BRAND_X, 10, ZONE_BRAND_X, HEADER_BOTTOM);
  line(ZONE_AGENT0_X, 10, ZONE_AGENT0_X, HEADER_BOTTOM);
  line(ZONE_AGENT1_X, 10, ZONE_AGENT1_X, HEADER_BOTTOM);

  // Zone 0 — brand name or back hint
  if (mode == OVERVIEW) {
    setFontLarge();
    textAtBold("hiClaude", safe_x + 8, 54, true);
  } else {
    setFontSmall();
    textAt("< 返回概览", safe_x + 12, 50);
  }

  // Zone 1 — agent 0 status (28px, baseline aligned with hiClaude)
  if (view.agent_count > 0) {
    const AgentView &a = view.agents[0];
    const String st = a.task_count > 0 ? a.tasks[0].status : "idle";
    const bool active = (st == "running" || st == "thinking" || st == "needs_action");
    drawStatusDot(ZONE_BRAND_X + 18, 44, active);
    setFontSmall();
    textAtBold(ellipsizeUtf8(a.label, 12), ZONE_BRAND_X + 36, 54, true);
    textAtRight(taskStatusShort(st), ZONE_AGENT0_X - 14, 54, false, true);
  }

  // Zone 2 — agent 1 status
  if (view.agent_count > 1) {
    const AgentView &a = view.agents[1];
    const String st = a.task_count > 0 ? a.tasks[0].status : "idle";
    const bool active = (st == "running" || st == "thinking" || st == "needs_action");
    drawStatusDot(ZONE_AGENT0_X + 18, 44, active);
    setFontSmall();
    textAtBold(ellipsizeUtf8(a.label, 12), ZONE_AGENT0_X + 36, 54, true);
    textAtRight(taskStatusShort(st), ZONE_AGENT1_X - 14, 54, false, true);
  }

  // Zone 3 — clock (tap to force refresh)
  setFontSmall();
  textAt2x(clockString(), ZONE_AGENT1_X + 30, 54);
}

void drawTaskItem(int32_t x, int32_t y, int32_t w, const String &status, const String &name,
                  bool separator, size_t max_title_chars = 7) {
  setFontSmall();
  textAtBold(taskStatusShort(status), x + 4, y + 40, true);

  const String title = name.length() ? name : "等待任务";
  setFontLarge();
  textAtBold(ellipsizeUtf8(title, max_title_chars), x + 92, y + 40, true);
  if (separator) {
    line(x + 92, y + 58, x + w - 8, y + 58);
  }
}

// Full-screen tasks-only view: shows up to 5 tasks, no quotas
void drawAgentTasksFull(int32_t x, int32_t y, int32_t w, int32_t h, const AgentView *agent) {
  rect(x, y, w, h, BLACK);

  const String label = agent ? agent->label : "Agent";
  setFontLarge();
  textAtBold(ellipsizeUtf8(label, 20), x + 22, y + 52, true);

  line(x + 22, y + 76, x + w - 22, y + 76);

  constexpr size_t MAX_TASKS = 5;
  constexpr int32_t ROW_H = 58;
  const size_t count = agent ? agent->task_count : 0;
  for (size_t i = 0; i < MAX_TASKS && i < count; ++i) {
    const int32_t row_y = y + 86 + static_cast<int32_t>(i) * ROW_H;
    const bool sep = (i + 1 < count && i + 1 < MAX_TASKS);
    drawTaskItem(x + 22, row_y, w - 44, agent->tasks[i].status, agent->tasks[i].name, sep, 22);
  }
  if (count == 0) {
    setFontSmall();
    textAt("等待任务", x + 26, y + 126);
  }
}

void drawAgentColumn(int32_t x, int32_t y, int32_t w, int32_t h, const AgentView *agent,
                     size_t max_title_chars = 7) {
  rect(x, y, w, h, BLACK);

  const String label = agent ? agent->label : "Agent";
  setFontLarge();
  textAtBold(ellipsizeUtf8(label, 13), x + 22, y + 52, true);

  for (size_t i = 0; i < 2; ++i) {
    const QuotaView *quota = agent && i < agent->quota_count ? &agent->quotas[i] : nullptr;
    const int32_t quota_y = y + 94 + static_cast<int32_t>(i) * 54;
    setFontLarge();
    textAt(quota ? ellipsizeUtf8(quota->label.length() ? quota->label : "额度", 5) : "额度", x + 24, quota_y);
    if (quota) {
      const String remaining = String((int)quota->remaining) + "/" + String((int)quota->limit);
      textAtRight(remaining, x + w - 24, quota_y, true);
      if (quota->reset.length()) textAt(quota->reset, x + 160, quota_y);
      drawBar(x + 24, quota_y + 14, w - 48, 16, quota->percent);
    } else {
      textAtRight("--", x + w - 24, quota_y, true);
      drawBar(x + 24, quota_y + 14, w - 48, 16, 0);
    }
  }

  line(x + 22, y + 192, x + w - 22, y + 192);

  for (size_t i = 0; i < 3; ++i) {
    const int32_t row_y = y + 202 + static_cast<int32_t>(i) * 60;
    if (agent && i < agent->task_count) {
      drawTaskItem(x + 22, row_y, w - 44, agent->tasks[i].status, agent->tasks[i].name, i < 2, max_title_chars);
    } else {
      drawTaskItem(x + 22, row_y, w - 44, "idle", "等待任务", i < 2, max_title_chars);
    }
  }
  const size_t extra_count = agent && agent->task_total_count > 3 ? agent->task_total_count - 3 : 0;
  if (extra_count > 0) {
    setFontSmall();
    textAtBold("+" + String(extra_count) + " 任务运行中", x + w - 168, y + 370);
  }
}

void drawBootScreen(const String &line1, const String &line2 = "") {
  clearFramebuffer();
  rect(12, 12, EPD_WIDTH - 24, EPD_HEIGHT - 24, BLACK);
  setFontLarge();
  textAt("hiClaude", 32, 64);
  line(32, 88, EPD_WIDTH - 32, 88);
  setFontBody();
  textAt(line1, 32, 154);
  if (line2.length()) {
    textAt(line2, 32, 214);
  }
  epd_poweron();
  epd_draw_grayscale_image(epd_full_screen(), framebuffer);
  epd_poweroff();
}

void drawState(const DisplayView &view, ViewMode mode = OVERVIEW) {
  clearFramebuffer();
  constexpr int32_t safe_x = 20;
  constexpr int32_t right = EPD_WIDTH - safe_x;
  rect(10, 10, EPD_WIDTH - 20, EPD_HEIGHT - 20, BLACK);

  drawHeader(view, mode);
  line(safe_x, HEADER_BOTTOM, right, HEADER_BOTTOM);

  constexpr int32_t column_y = 104;
  constexpr int32_t column_h = 380;

  if (mode == OVERVIEW) {
    constexpr int32_t column_gap = 20;
    constexpr int32_t column_w = (EPD_WIDTH - safe_x * 2 - column_gap) / 2;
    const AgentView *agent0 = view.agent_count > 0 ? &view.agents[0] : nullptr;
    const AgentView *agent1 = view.agent_count > 1 ? &view.agents[1] : nullptr;
    drawAgentColumn(safe_x, column_y, column_w, column_h, agent0, 9);
    drawAgentColumn(safe_x + column_w + column_gap, column_y, column_w, column_h, agent1, 9);
  } else {
    const size_t agent_idx = (mode == AGENT1_FULL) ? 1 : 0;
    const AgentView *agent = agent_idx < view.agent_count ? &view.agents[agent_idx] : nullptr;
    drawAgentTasksFull(safe_x, column_y, right - safe_x, column_h, agent);
  }

  line(safe_x, 506, right, 506);
  setFontSmall();
  if (view.updated_at.length()) {
    textAt("updated " + ellipsize(view.updated_at.substring(0, 19), 22), safe_x, 524);
  }
  textAt("4.7in / 960x540", right - 170, 524);

  epd_poweron();
  epd_clear();
  epd_draw_grayscale_image(epd_full_screen(), framebuffer);
  epd_poweroff();
}

void handleTouch(const DisplayView &view) {
  int16_t tx_arr[1], ty_arr[1];
  const bool pressed = touch_ctrl.getPoint(tx_arr, ty_arr, 1) > 0;

  if (!pressed) {
    touch_active = false;  // finger lifted — ready for next tap
    return;
  }
  if (touch_active) return;  // still holding — ignore until released
  touch_active = true;

  // GT911 panel is rotated 90° vs the landscape display: its raw Y axis
  // is the screen's X axis (no mirror). Empirically rawY ~40..871 spans
  // screen X 0..960. Routing only needs screen X (zones are full-height).
  const int32_t raw_y = (int32_t)ty_arr[0];
  int32_t tx = (raw_y - 40) * 960 / 831;
  if (tx < 0) tx = 0;
  if (tx > EPD_WIDTH - 1) tx = EPD_WIDTH - 1;
  Serial.printf("touch raw(x=%d y=%d) -> screenX=%d (mode=%d)\n",
                (int)tx_arr[0], (int)ty_arr[0], (int)tx, (int)current_mode);

  // Route by X column; full-screen height is touchable
  if (tx >= ZONE_AGENT1_X) {
    last_refresh_ms = 0;  // force data refresh
  } else if (tx >= ZONE_AGENT0_X) {
    current_mode = (current_mode == AGENT1_FULL) ? OVERVIEW : AGENT1_FULL;
    if (view_valid) drawState(view, current_mode);
  } else if (tx >= ZONE_BRAND_X) {
    current_mode = (current_mode == AGENT0_FULL) ? OVERVIEW : AGENT0_FULL;
    if (view_valid) drawState(view, current_mode);
  } else {
    if (current_mode != OVERVIEW) {
      current_mode = OVERVIEW;
      if (view_valid) drawState(view, current_mode);
    }
  }
}

void readQuotaWindow(JsonObject quota, QuotaView &target, const char *fallback_label) {
  target.label = quota["label"] | fallback_label;
  target.remaining = quota["remaining"] | 0.0;
  target.limit = quota["limit"] | 0.0;
  target.percent = constrain(quota["percent"] | 0, 0, 100);
  target.reset = quota["reset_at"] | "";
}

void readAgentGroup(JsonObject item, AgentView &agent, const char *fallback_label) {
  agent.label = item["label"] | fallback_label;

  agent.quota_count = 0;
  JsonObject quota = item["quota"].as<JsonObject>();
  if (!quota.isNull()) {
    JsonObject five_hour = quota["five_hour"].as<JsonObject>();
    if (!five_hour.isNull() && agent.quota_count < 2) {
      readQuotaWindow(five_hour, agent.quotas[agent.quota_count++], "5小时额度");
    }
    JsonObject weekly = quota["weekly"].as<JsonObject>();
    if (!weekly.isNull() && agent.quota_count < 2) {
      readQuotaWindow(weekly, agent.quotas[agent.quota_count++], "周额度");
    }
  }

  agent.task_count = 0;
  agent.task_total_count = 0;
  for (JsonObject task_item : item["tasks"].as<JsonArray>()) {
    agent.task_total_count++;
    if (agent.task_count >= 5) {
      continue;
    }
    auto &target = agent.tasks[agent.task_count++];
    target.name = task_item["name"] | "等待任务";
    target.status = task_item["status"] | "idle";
  }
}

bool connectWiFi() {
  if (String(WIFI_SSID).isEmpty()) {
    drawBootScreen("Wi-Fi SSID is not configured", "Edit src/config_private.h");
    return false;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to Wi-Fi SSID: %s\n", WIFI_SSID);

  const uint32_t started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < WIFI_TIMEOUT_MS) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi connection failed");
    drawBootScreen("Wi-Fi connection failed", WIFI_SSID);
    return false;
  }

  Serial.print("Wi-Fi connected. IP: ");
  Serial.println(WiFi.localIP());
  return true;
}

bool fetchState(DisplayView &view) {
  HTTPClient http;
  http.setTimeout(10000);
  Serial.printf("Fetching %s\n", STATE_URL);

  if (!http.begin(STATE_URL)) {
    Serial.println("HTTP begin failed");
    return false;
  }

  const int code = http.GET();
  if (code != HTTP_CODE_OK) {
    Serial.printf("HTTP GET failed: %d\n", code);
    http.end();
    return false;
  }

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, http.getStream());
  http.end();

  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return false;
  }

  JsonObject task = doc["task"];
  view.task_name = task["name"] | "Waiting for task";
  view.status = task["status"] | "idle";
  view.status_label = task["status_label"] | "";
  view.detail = task["detail"] | "";
  view.progress = constrain(task["progress"] | 0, 0, 100);
  view.updated_at = doc["updated_at"] | "";

  view.task_count = 0;
  view.task_total_count = 0;
  JsonArray tasks = doc["tasks"].as<JsonArray>();
  if (!tasks.isNull()) {
    for (JsonObject item : tasks) {
      view.task_total_count++;
      if (view.task_count >= 3) {
        continue;
      }
      auto &target = view.tasks[view.task_count++];
      target.name = item["name"] | "等待任务";
      target.status = item["status"] | "idle";
    }
  }
  if (view.task_count == 0) {
    view.tasks[0].name = view.task_name;
    view.tasks[0].status = view.status;
    view.task_count = 1;
    view.task_total_count = 1;
  }

  view.quota_count = 0;
  for (JsonObject quota : doc["quotas"].as<JsonArray>()) {
    if (view.quota_count >= 2) {
      break;
    }
    auto &target = view.quotas[view.quota_count++];
    target.label = quota["label"] | quota["agent"] | "Agent";
    target.remaining = quota["remaining"] | 0.0;
    target.limit = quota["limit"] | 0.0;
    target.percent = constrain(quota["percent"] | 0, 0, 100);
    target.reset = quota["reset_at"] | "";
  }

  view.agent_count = 0;
  JsonObject claude_group = doc["claude_code"].as<JsonObject>();
  if (!claude_group.isNull() && view.agent_count < 2) {
    readAgentGroup(claude_group, view.agents[view.agent_count++], "Claude Code");
  }
  JsonObject codex_group = doc["codex"].as<JsonObject>();
  if (!codex_group.isNull() && view.agent_count < 2) {
    readAgentGroup(codex_group, view.agents[view.agent_count++], "Codex");
  }

  JsonObject groups = doc["groups"].as<JsonObject>();
  if (view.agent_count == 0 && !groups.isNull()) {
    JsonObject claude = groups["claude_code"].as<JsonObject>();
    if (!claude.isNull() && view.agent_count < 2) {
      readAgentGroup(claude, view.agents[view.agent_count++], "Claude Code");
    }
    JsonObject codex = groups["codex"].as<JsonObject>();
    if (!codex.isNull() && view.agent_count < 2) {
      readAgentGroup(codex, view.agents[view.agent_count++], "Codex");
    }
  }

  JsonArray agents = doc["agents"].as<JsonArray>();
  if (view.agent_count == 0 && !agents.isNull()) {
    for (JsonObject item : agents) {
      if (view.agent_count >= 2) {
        break;
      }
      auto &agent = view.agents[view.agent_count++];
      agent.label = item["label"] | item["agent"] | "Agent";

      agent.quota_count = 0;
      for (JsonObject quota : item["quotas"].as<JsonArray>()) {
        if (agent.quota_count >= 2) {
          break;
        }
        auto &target = agent.quotas[agent.quota_count++];
        target.label = quota["label"] | quota["window"] | "额度";
        target.remaining = quota["remaining"] | 0.0;
        target.limit = quota["limit"] | 0.0;
        target.percent = constrain(quota["percent"] | 0, 0, 100);
        target.reset = quota["reset_at"] | "";
      }

      agent.task_count = 0;
      agent.task_total_count = 0;
      for (JsonObject task_item : item["tasks"].as<JsonArray>()) {
        agent.task_total_count++;
        if (agent.task_count >= 5) {
          continue;
        }
        auto &target = agent.tasks[agent.task_count++];
        target.name = task_item["name"] | "等待任务";
        target.status = task_item["status"] | "idle";
      }
    }
  }

  if (view.agent_count == 0) {
    view.agent_count = min(view.quota_count, static_cast<size_t>(2));
    if (view.agent_count == 0) {
      view.agent_count = 1;
    }
    for (size_t i = 0; i < view.agent_count; ++i) {
      auto &agent = view.agents[i];
      if (i < view.quota_count) {
        agent.label = view.quotas[i].label;
        agent.quotas[0] = view.quotas[i];
        agent.quota_count = 1;
      }
      if (i == 0) {
        agent.task_count = view.task_count;
        agent.task_total_count = view.task_total_count;
        for (size_t task_index = 0; task_index < view.task_count && task_index < 3; ++task_index) {
          agent.tasks[task_index] = view.tasks[task_index];
        }
      }
    }
  }

  return true;
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("hiClaude LilyGo T5-ePaper-S3 firmware");

  framebuffer = static_cast<uint8_t *>(ps_calloc(EPD_WIDTH * EPD_HEIGHT / 2, sizeof(uint8_t)));
  if (!framebuffer) {
    Serial.println("PSRAM framebuffer allocation failed");
    while (true) {
      delay(1000);
    }
  }

  epd_init();
  u8g2.begin(canvas);
  u8g2.setFontMode(1);
  u8g2.setFontDirection(0);
  u8g2.setForegroundColor(1);
  u8g2.setBackgroundColor(0);
  epd_poweron();
  epd_clear();
  epd_poweroff();

  Wire.begin(BOARD_SDA, BOARD_SCL);
  touch_ctrl.setPins(-1, TOUCH_INT);
  bool touch_ok = touch_ctrl.begin(Wire, GT911_SLAVE_ADDRESS_L)
               || touch_ctrl.begin(Wire, GT911_SLAVE_ADDRESS_H);
  Serial.println(touch_ok ? "Touch GT911 initialized" : "Touch init failed (non-fatal)");

  if (connectWiFi()) {
    syncNTP();
    last_refresh_ms = 0;
  }
}

void loop() {
  handleTouch(g_view);

  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (millis() - last_refresh_ms >= REFRESH_INTERVAL_MS || last_refresh_ms == 0) {
    if (fetchState(g_view)) {
      view_valid = true;
      drawState(g_view, current_mode);
    } else {
      drawBootScreen("State fetch failed", STATE_URL);
    }
    last_refresh_ms = millis();
  }

  delay(100);  // reduced from 1000ms for touch responsiveness
}
