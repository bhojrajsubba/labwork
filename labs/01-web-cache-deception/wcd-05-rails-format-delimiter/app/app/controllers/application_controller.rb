class ApplicationController < ActionController::Base
  skip_forgery_protection

  helper_method :current_user, :current_username, :lab_mode

  USERS = {
    "victim" => {
      password: "P@sswordVictim2026!",
      name: "Dr. Alex Mercer",
      email: "alex.mercer@corp.internal",
      role: "Director of Cloud Infrastructure",
      api_key: "sk-live-vault-mercer-9938210948ab12e8",
      flag: "FLAG{wcd_r41ls_d0t_f0rm4t_d3l1m1t3r_c4ch3}",
      balance: "$2,450,000.00"
    },
    "attacker" => {
      password: "attacker123",
      name: "Robin Vance",
      email: "robin@external.org",
      role: "Security Researcher",
      api_key: "sk-test-attacker-key-3871",
      flag: "FLAG{keep_trying_attacker}",
      balance: "$25.00"
    }
  }.freeze

  def lab_mode
    ENV.fetch("MODE", "vulnerable").downcase
  end

  def current_username
    user = session[:user]
    user if user && USERS.key?(user)
  end

  def current_user
    username = current_username
    username ? USERS[username] : nil
  end
end
