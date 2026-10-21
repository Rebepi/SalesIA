import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const UploadIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="upload"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const arrowTransform = !isReduced && isActive ? "translateY(-2px)" : "translateY(0)";
      return (
        <g>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <g
            style={{
              transform: arrowTransform,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          >
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </g>
        </g>
      );
    }}
  />
);
