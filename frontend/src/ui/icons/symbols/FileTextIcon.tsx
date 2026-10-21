import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const FileTextIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fileText"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      return (
        <g>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line
            x1="16"
            y1="13"
            x2="8"
            y2="13"
            style={{
              opacity: !isReduced && isActive ? 0.7 : 1,
              transition: isReduced ? "none" : "opacity 220ms ease-out"
            }}
          />
          <line x1="16" y1="17" x2="8" y2="17" />
        </g>
      );
    }}
  />
);
