import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ExpandIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="expand"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const expandTransform = !isReduced && isActive ? "scale(1.08)" : "scale(1)";
      return (
        <g
          style={{
            transform: expandTransform,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="m21 21-6-6m6 6v-4.8m0 4.8h-4.8" />
          <path d="M3 15v6h6" />
          <path d="M21 9V3h-6" />
          <path d="M9 3H3v6" />
        </g>
      );
    }}
  />
);
