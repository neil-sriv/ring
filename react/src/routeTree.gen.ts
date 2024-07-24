/* prettier-ignore-start */

/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file is auto-generated by TanStack Router

// Import Routes

import { Route as rootRoute } from "./routes/__root";
import { Route as ResetPasswordImport } from "./routes/reset-password";
import { Route as RecoverPasswordImport } from "./routes/recover-password";
import { Route as LoginImport } from "./routes/login";
import { Route as LayoutImport } from "./routes/_layout";
import { Route as LayoutIndexImport } from "./routes/_layout/index";
import { Route as LayoutSettingsImport } from "./routes/_layout/settings";
import { Route as LayoutGroupsImport } from "./routes/_layout/groups";
import { Route as LayoutAdminImport } from "./routes/_layout/admin";
import { Route as LayoutLoopsLoopIdImport } from "./routes/_layout/loops/$loopId";
import { Route as LayoutGroupsGroupIdLoopsImport } from "./routes/_layout/groups_/$groupId/loops";

// Create/Update Routes

const ResetPasswordRoute = ResetPasswordImport.update({
  path: "/reset-password",
  getParentRoute: () => rootRoute,
} as any);

const RecoverPasswordRoute = RecoverPasswordImport.update({
  path: "/recover-password",
  getParentRoute: () => rootRoute,
} as any);

const LoginRoute = LoginImport.update({
  path: "/login",
  getParentRoute: () => rootRoute,
} as any);

const LayoutRoute = LayoutImport.update({
  id: "/_layout",
  getParentRoute: () => rootRoute,
} as any);

const LayoutIndexRoute = LayoutIndexImport.update({
  path: "/",
  getParentRoute: () => LayoutRoute,
} as any);

const LayoutSettingsRoute = LayoutSettingsImport.update({
  path: "/settings",
  getParentRoute: () => LayoutRoute,
} as any);

const LayoutGroupsRoute = LayoutGroupsImport.update({
  path: "/groups",
  getParentRoute: () => LayoutRoute,
} as any);

const LayoutAdminRoute = LayoutAdminImport.update({
  path: "/admin",
  getParentRoute: () => LayoutRoute,
} as any);

const LayoutLoopsLoopIdRoute = LayoutLoopsLoopIdImport.update({
  path: "/loops/$loopId",
  getParentRoute: () => LayoutRoute,
} as any);

const LayoutGroupsGroupIdLoopsRoute = LayoutGroupsGroupIdLoopsImport.update({
  path: "/groups/$groupId/loops",
  getParentRoute: () => LayoutRoute,
} as any);

// Populate the FileRoutesByPath interface

declare module "@tanstack/react-router" {
  interface FileRoutesByPath {
    "/_layout": {
      preLoaderRoute: typeof LayoutImport;
      parentRoute: typeof rootRoute;
    };
    "/login": {
      preLoaderRoute: typeof LoginImport;
      parentRoute: typeof rootRoute;
    };
    "/recover-password": {
      preLoaderRoute: typeof RecoverPasswordImport;
      parentRoute: typeof rootRoute;
    };
    "/reset-password": {
      preLoaderRoute: typeof ResetPasswordImport;
      parentRoute: typeof rootRoute;
    };
    "/_layout/admin": {
      preLoaderRoute: typeof LayoutAdminImport;
      parentRoute: typeof LayoutImport;
    };
    "/_layout/groups": {
      preLoaderRoute: typeof LayoutGroupsImport;
      parentRoute: typeof LayoutImport;
    };
    "/_layout/settings": {
      preLoaderRoute: typeof LayoutSettingsImport;
      parentRoute: typeof LayoutImport;
    };
    "/_layout/": {
      preLoaderRoute: typeof LayoutIndexImport;
      parentRoute: typeof LayoutImport;
    };
    "/_layout/loops/$loopId": {
      preLoaderRoute: typeof LayoutLoopsLoopIdImport;
      parentRoute: typeof LayoutImport;
    };
    "/_layout/groups/$groupId/loops": {
      preLoaderRoute: typeof LayoutGroupsGroupIdLoopsImport;
      parentRoute: typeof LayoutImport;
    };
  }
}

// Create and export the route tree

export const routeTree = rootRoute.addChildren([
  LayoutRoute.addChildren([
    LayoutAdminRoute,
    LayoutGroupsRoute,
    LayoutSettingsRoute,
    LayoutIndexRoute,
    LayoutLoopsLoopIdRoute,
    LayoutGroupsGroupIdLoopsRoute,
  ]),
  LoginRoute,
  RecoverPasswordRoute,
  ResetPasswordRoute,
]);

/* prettier-ignore-end */
