import { useRouter } from "next/navigation";
import { LoginFormStateType } from "../ui/login-form";

export async function authenticate(
  prevState: LoginFormStateType,
  formData: FormData
): Promise<LoginFormStateType> {
  return await fetch("/api/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      accept: "application/json",
    },
    body: new URLSearchParams({
      username: formData.get("email"),
      password: formData.get("password"),
    }),
  })
    .then(async (response) => {
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("accessToken", data.access_token);
        localStorage.setItem("tokenType", data.token_type);
        return {
          accessToken: data.access_token,
          tokenType: data.token_type,
        };
      } else {
        throw new Error(data.detail);
      }
    })
    .catch((error) => {
      return { error: error.message };
    });
}
