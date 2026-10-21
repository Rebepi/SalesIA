import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const GripVerticalIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="gripVertical"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const scaleDots = !isReduced && isActive ? "scale(1.1)" : "scale(1)";
      return (
        <g
          style={{
            transform: scaleDots,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 160ms ${MOTION_EASINGS.standard}`
          }}
        >
          <circle cx="9" cy="12" r="1" />
          <circle cx="9" cy="5" r="1" />
          <circle cx="9" cy="19" r="1" />
          <circle cx="15" cy="12" r="1" />
          <circle cx="15" cy="5" r="1" />
          <circle cx="15" cy="19" r="1" />
        </g>
      );
    }}
  />
);
