import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const UndoIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="undo"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftTransform = !isReduced && isActive ? "translateX(-2px)" : "translateX(0)";
      return (
        <g
          style={{
            transform: shiftTransform,
            transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M3 7v6h6" />
          <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" />
        </g>
      );
    }}
  />
);
