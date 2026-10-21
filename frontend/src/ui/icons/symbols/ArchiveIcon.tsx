import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ArchiveIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="archive"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const lidTransform = !isReduced && isActive ? "translateY(-2px)" : "translateY(0)";
      return (
        <g>
          <rect
            width="20"
            height="5"
            x="2"
            y="3"
            rx="1"
            style={{
              transform: lidTransform,
              transition: isReduced ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
            }}
          />
          <path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" />
          <path d="M10 12h4" />
        </g>
      );
    }}
  />
);
