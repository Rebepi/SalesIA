import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ClockIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="clock"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const handRotation = !isReduced && isActive ? "rotate(45deg)" : "rotate(0deg)";
      return (
        <g>
          <circle cx="12" cy="12" r="10" />
          <polyline
            points="12 6 12 12 16 14"
            style={{
              transform: handRotation,
              transformOrigin: "12px 12px",
              transition: isReduced ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
