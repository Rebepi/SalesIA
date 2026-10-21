import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const TrashIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="trash"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shake = !isReduced && isActive ? "rotate(4deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: shake,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M3 6h18" />
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
        </g>
      );
    }}
  />
);
