import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const DownloadIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="download"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const arrowTransform = !isReduced && isActive ? "translateY(2px)" : "translateY(0)";
      return (
        <g>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <g
            style={{
              transform: arrowTransform,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          >
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </g>
        </g>
      );
    }}
  />
);
