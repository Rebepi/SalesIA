import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const SearchIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="search"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const tiltTransform = !isReduced && isActive ? "rotate(-10deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: tiltTransform,
            transformOrigin: "11px 11px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </g>
      );
    }}
  />
);
