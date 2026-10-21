import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ArrowRightIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="arrowRight"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shift = !isReduced && isActive ? "translateX(2px)" : "translateX(0)";
      return (
        <g
          style={{
            transform: shift,
            transition: isReduced ? "none" : `transform 140ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M5 12h14" />
          <path d="m12 5 7 7-7 7" />
        </g>
      );
    }}
  />
);
