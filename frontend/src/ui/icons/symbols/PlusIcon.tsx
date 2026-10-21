import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const PlusIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="plus"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const scaleTransform = !isReduced && isActive ? "scale(1.08)" : "scale(1)";
      return (
        <g
          style={{
            transform: scaleTransform,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M5 12h14" />
          <path d="M12 5v14" />
        </g>
      );
    }}
  />
);
