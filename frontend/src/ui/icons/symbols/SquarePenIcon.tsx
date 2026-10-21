import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const SquarePenIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="squarePen"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const penTransform = !isReduced && isActive ? "rotate(-10deg) translate(-1px, 1px)" : "none";
      const strokeDashoffset = !isReduced && isActive ? 4 : 0;
      return (
        <g>
          <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path
            d="M18.375 2.625a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4Z"
            style={{
              transform: penTransform,
              transformOrigin: "18px 4px",
              transition: isReduced ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
            }}
          />
          <path
            d="m9 15 2 2"
            style={{
              strokeDasharray: 8,
              strokeDashoffset,
              transition: isReduced ? "none" : "stroke-dashoffset 240ms ease-out"
            }}
          />
        </g>
      );
    }}
  />
);
