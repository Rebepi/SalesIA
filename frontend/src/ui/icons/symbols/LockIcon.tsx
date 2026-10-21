import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const LockIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="lock"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shackle = !isReduced && isActive ? "translateY(-1.5px)" : "translateY(0)";
      return (
        <g>
          <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
          <path
            d="M7 11V7a5 5 0 0 1 10 0v4"
            style={{
              transform: shackle,
              transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
