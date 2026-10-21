import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const RedoIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="redo"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftTransform = !isReduced && isActive ? "translateX(2px)" : "translateX(0)";
      return (
        <g
          style={{
            transform: shiftTransform,
            transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M21 7v6h-6" />
          <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7" />
        </g>
      );
    }}
  />
);
