import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const EyeIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="eye"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const pupilTransform = !isReduced && isActive ? "scale(1.15)" : "scale(1)";
      return (
        <g>
          <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
          <circle
            cx="12"
            cy="12"
            r="3"
            style={{
              transform: pupilTransform,
              transformOrigin: "12px 12px",
              transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
