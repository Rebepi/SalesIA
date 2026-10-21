import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CircleHelpIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="circleHelp"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const pulse = !isReduced && isActive ? "scale(1.08)" : "scale(1)";
      return (
        <g>
          <circle cx="12" cy="12" r="10" />
          <path
            d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"
            style={{
              transform: pulse,
              transformOrigin: "12px 10px",
              transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
            }}
          />
          <path d="M12 17h.01" />
        </g>
      );
    }}
  />
);
