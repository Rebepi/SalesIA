import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BellIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="bell"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const swayTransform = !isReduced && isActive ? "rotate(8deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: swayTransform,
            transformOrigin: "12px 3px",
            transition: isReduced ? "none" : `transform 260ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </g>
      );
    }}
  />
);
