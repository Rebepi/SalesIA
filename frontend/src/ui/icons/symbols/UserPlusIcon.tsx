import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const UserPlusIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="userPlus"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const pulsePlus = !isReduced && isActive ? "scale(1.15)" : "scale(1)";
      return (
        <g>
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="8.5" cy="7" r="4" />
          <g
            style={{
              transform: pulsePlus,
              transformOrigin: "20px 11px",
              transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
            }}
          >
            <line x1="20" y1="8" x2="20" y2="14" />
            <line x1="23" y1="11" x2="17" y2="11" />
          </g>
        </g>
      );
    }}
  />
);
