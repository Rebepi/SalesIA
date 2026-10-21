import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const LinkChainIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="link"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const joinLinks = !isReduced && isActive ? "scale(0.96)" : "scale(1)";
      return (
        <path
          d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"
          style={{
            transform: joinLinks,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        />
      );
    }}
  />
);
