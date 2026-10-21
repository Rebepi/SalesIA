import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const SendActionIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="send"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const flight = !isReduced && isActive ? "translate(1.5px, -1px) rotate(5deg)" : "none";
      return (
        <g
          style={{
            transform: flight,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </g>
      );
    }}
  />
);
