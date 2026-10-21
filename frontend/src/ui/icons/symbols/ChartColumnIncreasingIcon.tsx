import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ChartColumnIncreasingIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="chartColumnIncreasing"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const barScale = !isReduced && isActive ? "scaleY(1.15)" : "scaleY(1)";
      return (
        <g>
          <line x1="12" y1="20" x2="12" y2="10" />
          <line
            x1="18"
            y1="20"
            x2="18"
            y2="4"
            style={{
              transform: barScale,
              transformOrigin: "18px 20px",
              transition: isReduced ? "none" : `transform 260ms ${MOTION_EASINGS.standard}`
            }}
          />
          <line x1="6" y1="20" x2="6" y2="16" />
        </g>
      );
    }}
  />
);
