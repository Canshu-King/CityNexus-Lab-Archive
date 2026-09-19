/**
 * Live journey + governed replan (reference 10).
 *
 * Traveller language only:
 *   发生了什么 / 哪些受影响 / 哪些不变 / 推荐怎么改 / 接受 / 仅调整今天 / 稍后提醒
 *
 * Internal vocabulary (Event, ReplanProposal, C4, PlanVersion, authority
 * envelope) never reaches this surface.  Accepting calls the governed accept
 * endpoint; nothing mutates the plan locally.
 */

import { useCallback, useEffect, useState } from "react";
import { useLocale } from "../../i18n/LocaleContext";
import {
  useAuthoritativePlans,
  useAuthoritativeTwin,
} from "../../api/v12Authoritative";

type Proposal = {
  id: string;
  status: string;
  hard_constraints_passed: boolean;
  locked_commitments_preserved: boolean;
  diff: { removed?: string[]; added?: string[] };
  explanation?: { impact_model?: string; summary?: string };
};

type Disruption = {
  id: string;
  type: string;
  severity: string;
  affected_activity_id: string | null;
  occurred_at: string;
  payload?: Record<string, unknown>;
};

const EVENT_COPY: Record<string, { zh: string; en: string }> = {
  CLOSURE: { zh: "有一处地点临时关闭", en: "A stop is temporarily closed" },
  WEATHER: { zh: "天气影响行程", en: "Weather is affecting the trip" },
  TRAFFIC_DELAY: { zh: "路上拥堵", en: "Traffic is delayed" },
  SCHEDULE_DELAY: { zh: "行程时间有变化", en: "The schedule has shifted" },
  SERVICE_UNAVAILABLE: { zh: "某项服务不可用", en: "A service is unavailable" },
  USER_CHANGE: { zh: "你更新了行程需求", en: "You changed a trip requirement" },
  OTHER: { zh: "行程有新情况", en: "Something changed" },
};
