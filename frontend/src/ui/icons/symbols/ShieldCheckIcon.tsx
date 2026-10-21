import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ShieldCheckIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="shieldCheck"
    renderPaths={(state, isReduced) => {
      const isSuccess = state === "success" || state === "hover" || state === "focus";
      return (
        <g>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path
            d="m9 12 2 2 4-4"
            style={{
              strokeDasharray: 12,
              strokeDashoffset: !isReduced && isSuccess ? 0 : 0,
              transition: isReduced ? "none" : `stroke-dashoffset 220ms ${MOTION_EASINGS.enter}`
            }}
          />
        </g>
      );
    }}
  />
);
