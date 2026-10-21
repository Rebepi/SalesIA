import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const TruckIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="truck"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const roll = !isReduced && isActive ? "translateX(2px)" : "translateX(0)";
      return (
        <g
          style={{
            transform: roll,
            transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
          }}
        >
          <rect width="16" height="13" x="1" y="3" />
          <polygon points="17 8 20 8 23 11 23 16 17 16 17 8" />
          <circle cx="5.5" cy="18.5" r="2.5" />
          <circle cx="18.5" cy="18.5" r="2.5" />
        </g>
      );
    }}
  />
);
