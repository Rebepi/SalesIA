import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const UsersGroupIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="users"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftRight = !isReduced && isActive ? "translateX(1px)" : "translateX(0)";
      return (
        <g>
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path
            d="M22 21v-2a4 4 0 0 0-3-3.87"
            style={{
              transform: shiftRight,
              transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
            }}
          />
          <path
            d="M16 3.13a4 4 0 0 1 0 7.75"
            style={{
              transform: shiftRight,
              transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
