# annbench_leaderboard_test

annbench_leaderboardのgithub actions + awsのテスト

- githubインタフェース上のSettings -> Secretsから
`AWS_ACCESS_KEY_ID`と`AWS_SECRET_ACCESS_KEY`を打ち込む
- ちなみにこれはマスターではなくEC2fullAccessのみをもつIAMを作ればいい。参考： `/home/matsui/documents/16.10to18-aws/20.02-iam_create_ec2
`

・・・と思ったが出来ないので、ローカルでこれを実行するだけ、という処理にするか。。。

とりあえず今はrun.pyをするとec2を自動的に立ち上げて計算してローカルに結果をもってきて鯖が自動的に消えてくれるのでそれを使えばいい