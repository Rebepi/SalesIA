import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CircleCheckIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="circleCheck"
    renderPaths={(state, isReduced) => {
      const isSuccess = state === "success" || state === "hover" || state === "focus";
      return (
        <g>
          <circle cx="12" cy="12" r="10" />
          <path
            d="m9 12 2 2 4-4"
            style={{
              strokeDasharray: 12,
              strokeDashoffset: !isReduced && isSuccess ? 0 : 0,
              transition: isReduced ? "none" : `stroke-dashoffset 240ms ${MOTION_EASINGS.enter}`
            }}
          />
        </g>
      );
    }}
  />
);
