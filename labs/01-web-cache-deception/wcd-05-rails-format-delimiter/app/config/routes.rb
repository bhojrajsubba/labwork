Rails.application.routes.draw do
  mode = ENV.fetch("MODE", "vulnerable").downcase

  root "vault#index"
  get  "/login",  to: "vault#login_form"
  post "/login",  to: "vault#login"
  get  "/logout", to: "vault#logout"
  get  "/report", to: "vault#report_form"
  post "/report", to: "vault#report"

  if mode == "secure"
    # SECURE: Explicitly disable implicit (.:format) extension matching
    get "/profile", to: "vault#profile", format: false
  else
    # VULNERABLE: Rails routes implicitly compile as /profile(.:format)
    # Unregistered format extensions (.avif, .woff2, .ejs) fall back to HTML!
    get "/profile", to: "vault#profile"
  end
end
