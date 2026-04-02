import { apiPost } from "./client";

export type LoginPayload = { email: string; password: string };

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    avatar_url: string;
  };
};

export function loginRequest(payload: LoginPayload) {
  return apiPost<LoginPayload, LoginResponse>("/auth/login", payload);
}
