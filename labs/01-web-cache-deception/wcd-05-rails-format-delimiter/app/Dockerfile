FROM ruby:3.3-slim

WORKDIR /app

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY Gemfile ./
RUN bundle install --jobs 4

COPY . .

EXPOSE 5000

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
