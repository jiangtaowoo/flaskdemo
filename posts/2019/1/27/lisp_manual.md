# 表达式求值
## 表达式
   + 单引号开始的表达式将作为整体, 不作求值处理
   + C-x C-e 求值 (C-u C-x C-e 求值内容将回显在当前光标后面, 其中 C-u 用 SPC-u 取代)
   
   
    #+BEGIN_SRC elisp
     (+ 2 4)
     fill-column
    #+END_SRC
   + 基本函数 (尝试对下面的内容求值, 观察缓冲区的输出内容)
   
   
    #+BEGIN_SRC elisp
      '(some thing in the list)
      (substring "Hello world" 3 7)
      (message "Hello world")
      (setq counter 1)
      (message "I am counter %d" (+ counter 1))
    #+END_SRC

## 求值实践
    #+BEGIN_SRC elisp
      ;;缓冲区名称, 缓冲区对应的文件名称
      (buffer-name)
      (buffer-file-name)
      ;;current-buffer 得到的是缓冲区本身, 而不是缓冲区的名字
      (current-buffer)
      (other-buffer)
      ;;切换缓冲区, switch-to-buffer 会在屏幕回显切换后的缓冲区, set-buffer 则不
      (switch-to-buffer (other-buffer))
      ;;缓冲区信息
      (buffer-size)
      (point)
      (point-min)
      (point-max)
      ;;(substring (current-buffer) (point-min) 10)
    #+END_SRC
    
# 函数定义
## defun 特殊表
   定义形式
    #+BEGIN_SRC elisp
      ;;函数定义格式
      (defun fun-name (args)
        "optional documents"
        (interactive argument-passing-info)
        body...)
      ;;实例
      (defun multi-by-seven (num)
        "multiple the input number by seven, and return the result"
        (* num 7))
      (multi-by-seven 3)
    #+END_SRC
## devar 初始化变量
    #+BEGIN_SRC elisp
      ;;样例
      (devar varname varinitvalue
         "variable documents")
    #+END_SRC
## 交互函数
   使用 interactive 交互
    #+BEGIN_SRC elisp
      ;;交互函数实例
      (defun multi-by-seven (num)
        "multiple the input number by seven, and return the result"
        (interactive "p")
        (message "The result is %d" (* num 7)))
      ;;交互测试 SPC-u 5 M-x multi-by-seven
      ;;也可以用 bind keys 序列调用
    #+END_SRC
   + interactive 选项
     - p 将 C-u 数字 M-x 按键序列中的数字绑定到函数参数
     - r 将光标所在区域的开始和结束值作为两个参数传递给函数
     - B 将 buffer 名称作为参数传递给函数
     多个选项用\n 分隔
	 
	 
    #+BEGIN_SRC elisp
      ;;交互函数实例
      (defun name-of-func (buffer, start, end)
        "multiple the input number by seven, and return the result"
        (interactive "BAppend to buffer: \nr")
        body-of-func...)
      ;;交互测试 SPC-u 5 M-x multi-by-seven
      ;;也可以用 bind keys 序列调用
    #+END_SRC
## 其他谓词
   + let
   
   
    #+BEGIN_SRC elisp
      ;;定义格式
      (let ((var1 expr1)
             (var2 expr2))
           body)
    #+END_SRC
   + if
   + save-excursion
## cons, car, cdr, nthcdr, setcar, setcdr
## Narrow 和 Widen
   + save-restriction 保存变窄缓冲区
   + what-line 函数
   
   
    #+BEGIN_SRC elisp
      ;;实例
      (defun what-line ()
        "documents"
        (interactive)
        (save-restriction
           (widen)
           (save-excursion
              (beginning-of-line)
              (message "Line %d" (+ 1 (count-lines 1 (point)))))))
    #+END_SRC
# 缓冲区相关函数
## beginning-of-buffer
    #+BEGIN_SRC elisp
      ;;样例
      (defun simplified-bob ()
         "simplified version of beginning-of-buffer"
         (interactive)
         (push-mark)
         (goto-char (point-min)))
    #+END_SRC

## mark-whole-buffer
    #+BEGIN_SRC elisp
      ;;样例
      (defun demonstrate-mwb ()
         "documents here"
         (interactive)
         (push-mark (point))
         (push-mark (point-max))
         (goto-char (point-min)))
    #+END_SRC
    
## append-to-buffer
    #+BEGIN_SRC elisp
      ;;样例
      (defun demonstrate-atb (buffer start end)
          "documents here"
          (interactive "BAppend to buffer: \nr")
          (let ((oldbuf (current-buffer)))
            (save-excursion
              (set-buffer (get-buffer-create buffer))
              (insert-buffer-substring oldbuf start end))))
    #+END_SRC

## copy-to-buffer
    #+BEGIN_SRC elisp
      ;;样例
      (defun demonstrate-ctb (buffer start end)
          "documents here"
          (interactive "BAppend to buffer: \nr")
          (let ((oldbuf (current-buffer)))
            (save-excursion
              (set-buffer (get-buffer-create buffer))
              (erase-buffer)
              (save-excursion
                (insert-buffer-substring oldbuf start end)))))
    #+END_SRC

## insert-buffer
    #+BEGIN_SRC elisp
      ;;样例, 从其他缓冲区拷贝内容到当前缓冲区, *b 表示只读缓冲区
      (defun demonstrate-ib (buffer)
          "documents here"
          (interactive "*bInsert buffer: ")
          (or (bufferp buffer)
              (setq buffer (get-buffer buffer)))
          (let (start end newmark)
            (save-excursion
              (save-excursion
                 (set-buffer buffer)
                 (setq start (point-min) end (point-max)))
              (insert-buffer-substring buffer start end)
              (setq newmark (point)))
            (push-mark newmark)))
    #+END_SRC

## beginning-of-buffer 可变参形式
    #+BEGIN_SRC elisp
      ;;样例, 从其他缓冲区拷贝内容到当前缓冲区, *b 表示只读缓冲区
      (defun demonstrate-opt-bob (&optional arg)
         "simplified version of beginning-of-buffer"
         (interactive "P")
         (push-mark)
         (goto-char 
            (if arg
                (if (> (buffer-size) 10000)
                    (* (prefix-numeric-value arg) (/ (buffer-size) 10))
                    (/ (+ 10 (* (buffer-size) (prefix-numeric-value arg))) 10))
                (point-min)))
         (if arg (forward-line 1)))
    #+END_SRC

# 文本操作
## kill ring 相关操作 zap-to-char
    #+BEGIN_SRC elisp
      ;;样例
      (defun demo-zap-to-char (char arg)
         "documents"
         (interactive "*p\ncZap to char: ")
         (kill-region (point)
                      (progn
                         (search-forward
                           (char-to-string char) nil nil arg)
                         (point))))
      ;;kill-region 的实现
      (defun demo-kill-region (beg end)
         "documents"
         (interactive "*r")
         (copy-region-as-kill beg end)
         (delete-region beg end))
    #+END_SRC
    
## copy-region-as-kill 函数实现
    #+BEGIN_SRC elisp
        ;;样例
        (defun demo-copy-region-as-kill (beg end)
           "documents"
           (interactive "r")
           (if (eq last-command 'kill-region)
               (kill-append (buffer-substring beg end) (< end beg))
               (setq kill-ring
                 (cons (buffer-substring beg end) kill-ring))
               (if (> (length kill-ring) kill-ring-max)
                   (setcdr (nthcdr (1- kill-ring-max) kill-ring) nil)))
           (setq this-command 'kill-region)
           (setq kill-ring-yank-pointer kill-ring))
    #+END_SRC

# 循环与递归
## while
   (while expr
     body)
## 递归

# 调试
## debug-on-error
   (setq debug-on-error t)
## debug-on-entry
   M-x debug-on-entry RET function-to-be-debugged RET
   按 d 逐语句调试
## debug-on-quit
## edebug
   M-x edebug-defun RET
   按 SPC 逐语句调试
   
# 编码练习
## mark region 测试
    #+BEGIN_SRC elisp
      (defun region_mark_ornot ()
        (message "beg=%d, end=%d" (region-beginning) (region-end)))
      (region_mark_ornot)
      ;;测试当前 buffer 是否已经有 mark 选区, 如果有, 返回选区位置, 否则返回当前单词位置
      (defun get-word-or-region ()
         "if mark exist, return beg, end;
          else return current word on cursor as region"
         (interactive)
         (let (beg end)
          (if (use-region-p)
              (setq beg (region-beginning) end (region-end))
              (save-excursion
                (skip-chars-backward "A-Za-z0-9")
                (setq beg (point))
                (skip-chars-forward "A-Za-z0-9")
                (setq end (point))))
          (buffer-substring beg end)
          ))
      (get-word-or-region)
      ;;获取当前 mark 选中的 region 或者当前光标所在的 word
      (defun get-word-or-region2 ()
        "Downcase current word or region."
      (interactive)
      (let (pos1 pos2 bds)
        (if (use-region-p)
          (setq pos1 (region-beginning) pos2 (region-end))
          (progn
            (setq bds (bounds-of-thing-at-point 'symbol))
            (setq pos1 (car bds) pos2 (cdr bds))))
        ;; now, pos1 and pos2 are the starting and ending positions of the
        ;; current word, or current text selection if exist.
        ;;(downcase-region pos1 pos2)
        (buffer-substring pos1 pos2)
        ))
      ;;使用
      (get-word-or-region2)

    #+END_SRC
## 调用 shell 脚本测试
   - 方法一: shell-command-on-region
   
   
    #+BEGIN_SRC elisp
      ;;调用外部 shell 脚本, 使用 shell-command-on-region
      (defun trans-word-or-region ()
        "translate the world through internet by calling python script"
        (interactive)
        (let (word)
          (setq word (get-word-or-region))
          (setq cmdStr (format "python %%HOME%%/uutrans.py %s" word))
          (shell-command-on-region (region-beginning) (region-end) cmdStr "*FlashCard*" nil nil t)
          ))
      (global-set-key (kbd "C-c t") 'trans-word-or-region)
    #+END_SRC

   - 方法二: start-process
   
   
    #+BEGIN_SRC elisp
      ;;使用 start-process
      (defun trans-word-or-region2 ()
        "translate the world through internet by calling python script"
        (interactive)
        (let (word)
          (setq word (get-word-or-region))
          (setq cmdStr (format "c:/greensoft/emacs25/uutrans.py"))
          (start-process "trans-sprocess" "*FlashCard*" "python" cmdStr word)
          ))
      (global-set-key (kbd "C-c t") 'trans-word-or-region2)
    #+END_SRC
## 阅读辅助翻译脚本
    #+BEGIN_SRC elisp
      ;;获取选区 region, 或者当前光标所在的单词
      (defun get-word-or-region ()
         "if mark exist, return beg, end;
          else return current word on cursor as region"
         (interactive)
         (let (beg end)
          (if (use-region-p)
              (setq beg (region-beginning) end (region-end))
              (save-excursion
                (skip-chars-backward "A-Za-z0-9")
                (setq beg (point))
                (skip-chars-forward "A-Za-z0-9")
                (setq end (point))))
          (buffer-substring-no-properties beg end)
          ))
      ;;使用 start-process 调用 python 脚本, 翻译选区单词
      (defun trans-word-or-region (word bufname)
        "translate the world through internet by calling python script"
        (interactive)
        (let (script)
          (cond ((eq system-type 'windows-nt) 
                   (setq script (format "c:/greensoft/emacs25/uutrans.py")))
                ((eq system-type 'gnu/linux) 
                   (setq script (format "/home/jtwu/uutrans.py"))))
          (start-process "trans-sprocess" bufname "python" script word)
          ))
      ;;处理 buffer 内容, 删除无效内容
      (defun prettify-flashcard (bufname)
         "delete last 4 lines of buffer *FlashCard*"
         (interactive)
          (save-excursion
            (set-buffer (get-buffer-create bufname))
            (progn
                (goto-char (point-max))
                (forward-line (- 3))
                (delete-region (point) (point-max)))))
      ;;检查是否已经有结果返回
      (defun check-flashcard (bufname)
         "return t if the translate result is in the buffer, else return nil"
         (interactive)
          (save-excursion
            (set-buffer (get-buffer-create bufname))
            (equal "Process trans-sprocess finished"
              (progn
                (goto-char (point-max))
                (if (> (count-lines (point-min) (point-max)) 0)
                  (progn
                    (forward-line (- 1))
                    (buffer-substring (point) (- (point-max) 1)))
                  ())))))
      ;;某个 buffer 是否包含指定字符串, 如果包含, 定位至该位置, 返回 t
      (defun buffer-contains-substring (bufname strfind)
        "if the buffer contains strfind, if yes, goto-char and return t"
        (interactive)
        (save-excursion
          (set-buffer (get-buffer-create bufname))
          (save-match-data
            (let (pos)
              (goto-char (point-min))
              (setq pos (search-forward strfind nil t))
              (if (not (eq pos nil)) 
                (progn 
                  (goto-char (- pos (length strfind)))
                  (set-window-point 
                    (get-buffer-window (current-buffer)) 
                    (- pos (length strfind)))))))))
      ;;阅读过程中调用的翻译函数
      (defun fly-translate ()
         "translate while reading by calling python script"
         (interactive)
         (let (word bufname waits)
           (setq word (get-word-or-region))
           (setq bufname "*FlashCard*")
           (setq waits 0)
           (trans-word-or-region word bufname)
           (while (and (< waits 10) (not (check-flashcard bufname))) 
                  (progn (setq waits (+ waits 1))
                     (sit-for 1)))
           (if (< waits 10)
               (prettify-flashcard bufname))
           (if (eq (length (window-list)) 1)
               (split-window-right 100))
           ;;(other-window 1)
           (display-buffer-use-some-window (get-buffer bufname) 
              '((side . right)))
           (buffer-contains-substring bufname word)))
      ;;绑定快捷键
      (global-set-key (kbd "C-c t") 'fly-translate)
      ;;测试代码
      (buffer-contains-substring "*FlashCard*" "properties")
      (equal (check-flashcard "*FlashCard*") "Process trans-sprocess finished")
      (prettify-flashcard "*FlashCard*")
      ;;(display-buffer-in-side-window "*FlashCard*" '((side . right)))
      (string-match-p (regexp-quote "translate") ("*FlashCard*"))
    #+END_SRC
