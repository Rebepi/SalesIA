import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ExternalLinkIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="externalLink"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftCorner = !isReduced && isActive ? "translate(1.5px, -1.5px)" : "none";
      return (
        <g>
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline
            points="15 3 21 3 21 9"
            style={{
              transform: shiftCorner,
              transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
            }}
          />
          <line
            x1="10"
            y1="14"
            x2="21"
            y2="3"
            style={{
              transform: shiftCorner,
              transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
