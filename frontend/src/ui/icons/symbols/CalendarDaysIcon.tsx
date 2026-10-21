import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CalendarDaysIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="calendarDays"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      return (
        <g>
          <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
          <path
            d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"
            style={{
              opacity: !isReduced && isActive ? 0.7 : 1,
              transition: isReduced ? "none" : "opacity 180ms ease-out"
            }}
          />
        </g>
      );
    }}
  />
);
