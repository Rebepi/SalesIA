import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BoxIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="box"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const lift = !isReduced && isActive ? "translateY(-1.5px)" : "translateY(0)";
      return (
        <g>
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline
            points="3.27 6.96 12 12.01 20.73 6.96"
            style={{
              transform: lift,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </g>
      );
    }}
  />
);
