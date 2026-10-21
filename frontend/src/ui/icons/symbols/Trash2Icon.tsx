import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const Trash2Icon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="trash2"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const lidLift = !isReduced && isActive ? "rotate(-18deg) translateY(-1px)" : "rotate(0deg) translateY(0)";
      return (
        <g>
          <g
            style={{
              transform: lidLift,
              transformOrigin: "4px 6px",
              transition: isReduced ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
            }}
          >
            <path d="M3 6h18" />
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </g>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </g>
      );
    }}
  />
);
