import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ChartLineIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="chartLine"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      return (
        <g>
          <path d="m3 3v18h18" />
          <path
            d="m19 9-5 5-4-4-3 3"
            style={{
              strokeDasharray: 24,
              strokeDashoffset: !isReduced && isActive ? 0 : 0,
              transition: isReduced ? "none" : `stroke-dashoffset 260ms ${MOTION_EASINGS.enter}`
            }}
          />
        </g>
      );
    }}
  />
);
