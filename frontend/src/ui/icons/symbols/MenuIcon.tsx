import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const MenuIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="menu"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftMid = !isReduced && isActive ? "translateX(1.5px)" : "translateX(0)";
      return (
        <g>
          <line x1="4" y1="6" x2="20" y2="6" />
          <line
            x1="4"
            y1="12"
            x2="20"
            y2="12"
            style={{
              transform: shiftMid,
              transition: isReduced ? "none" : `transform 160ms ${MOTION_EASINGS.standard}`
            }}
          />
          <line x1="4" y1="18" x2="20" y2="18" />
        </g>
      );
    }}
  />
);
