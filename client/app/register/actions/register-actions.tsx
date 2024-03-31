import { RegisterFormStateType } from "../ui/register-form";

export async function register(
  prevState: RegisterFormStateType,
  formData: FormData
): Promise<RegisterFormStateType> {
  return await fetch("/api/user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      accept: "application/json",
    },
    body: JSON.stringify({
      email: formData.get("email"),
      name: formData.get("name"),
      password: formData.get("password"),
    }),
  })
    .then(async (response) => {
      const data = await response.json();
      if (response.ok) {
        return {
          apiIdentifier: data.api_identifier,
        };
      } else {
        throw new Error(data.detail);
      }
    })
    .catch((error) => {
      return { error: error.message };
    });
}
