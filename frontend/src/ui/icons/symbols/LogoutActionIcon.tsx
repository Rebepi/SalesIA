import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const LogoutActionIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="logout"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftExit = !isReduced && isActive ? "translateX(2px)" : "translateX(0)";
      return (
        <g>
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <g
            style={{
              transform: shiftExit,
              transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
            }}
          >
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </g>
        </g>
      );
    }}
  />
);
