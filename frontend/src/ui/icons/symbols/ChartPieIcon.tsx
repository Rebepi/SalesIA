import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ChartPieIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="chartPie"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const rotateSlice = !isReduced && isActive ? "rotate(15deg)" : "rotate(0deg)";
      return (
        <g>
          <path d="M21.21 15.89A10 10 0 1 1 8 2.83" />
          <path
            d="M22 12A10 10 0 0 0 12 2v10z"
            style={{
              transform: rotateSlice,
              transformOrigin: "12px 12px",
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
