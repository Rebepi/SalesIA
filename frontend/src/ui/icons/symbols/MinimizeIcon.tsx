import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const MinimizeIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="minimize"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shrinkTransform = !isReduced && isActive ? "scale(0.92)" : "scale(1)";
      return (
        <g
          style={{
            transform: shrinkTransform,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="m8 8 6 6m-6-6v4.8m0-4.8h4.8" />
          <path d="M16 16v-6h-6" />
          <path d="M8 16H2v6" />
          <path d="M16 8V2h6" />
        </g>
      );
    }}
  />
);
