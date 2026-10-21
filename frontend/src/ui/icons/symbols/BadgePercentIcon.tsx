import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BadgePercentIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="badgePercent"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const tilt = !isReduced && isActive ? "rotate(10deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: tilt,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="m3.85 8.62 1.4-1.4a2 2 0 0 1 2.83 0L12 11.08l3.92-3.86a2 2 0 0 1 2.83 0l1.4 1.4a2 2 0 0 1 0 2.83L16.29 15.3l3.86 3.92a2 2 0 0 1 0 2.83l-1.4 1.4a2 2 0 0 1-2.83 0L12 19.59l-3.92 3.86a2 2 0 0 1-2.83 0l-1.4-1.4a2 2 0 0 1 0-2.83L7.71 15.3 3.85 11.45a2 2 0 0 1 0-2.83Z" />
          <line x1="15" y1="9" x2="9" y2="15" />
        </g>
      );
    }}
  />
);
