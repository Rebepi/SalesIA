import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CopyIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="copy"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed" || state === "success";
      const frontTransform = !isReduced && isActive ? "translate(1.5px, -1.5px)" : "none";
      return (
        <g>
          <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
          <path
            d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"
            style={{
              transform: frontTransform,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
