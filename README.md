# Group 1 - Web Data Processing Systems
[Please describe briefly how your system works, which existing tools you have used and why, and how to run your solution.]



## Git cheatsheet

## Check status
To see files what files are staged to be pushed to git type:

```bash
git status
```


### Pull latest code
```bash
git pull
```


### Push new code
```bash
git add <changed_files>
git commit -m "commit message"
git push
```

The first time you might have to run the following command instead of `git push` to configure git properly:
```bash
git push -u origin master
```


If you get an error about local changes then you have to merge your local code with the code on github:

1. Stash your local code:
```bash
git stash
```
2. Pull the latest code from the github sever:
```bash
git pull
```
3. Merge (hopefully happens automatically, if a conflict happens you need to go into the relevant file and fix it yourself):
```bash
git stash pop
```

If there were no conflicts or you manually fixed them, you can now push the merged code to github (see section "Push new code")

## When own version is not good anymore 
```git pull 
```git fetch - - all
```git reset --hard origin/master
```git pull  
