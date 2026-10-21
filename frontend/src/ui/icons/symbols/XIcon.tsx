import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const XIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="x"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const rotation = !isReduced && isActive ? "rotate(8deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: rotation,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 140ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </g>
      );
    }}
  />
);
