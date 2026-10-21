import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BoxesIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="boxes"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      return (
        <g
          style={{
            transform: !isReduced && isActive ? "scale(1.05)" : "scale(1)",
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="m21.12 6.4-6.05-3.67a2 2 0 0 0-2.14 0L6.88 6.4A2 2 0 0 0 5.8 8.13v7.74a2 2 0 0 0 1.08 1.73l6.05 3.67a2 2 0 0 0 2.14 0l6.05-3.67a2 2 0 0 0 1.08-1.73V8.13a2 2 0 0 0-1.08-1.73Z" />
          <line x1="12" y1="22" x2="12" y2="12" />
          <polyline points="21 7 12 12 3 7" />
        </g>
      );
    }}
  />
);
