exec(open(__file__.replace('inspect_grid','inspect_before')).read().split('for page')[0])
for page in range(8):
    board=Image.new('RGB',(1440,1120),'#cdd6cc');d=ImageDraw.Draw(board)
    for row,p in enumerate(residents('characters')[page*5:page*5+5]):
        a,_=prepare_human(p);tile=Image.fromarray(a).crop((38,100,218,156)).resize((720,224),Image.Resampling.NEAREST)
        board.paste(tile,(0,row*224),tile);d.text((4,row*224),p.name,fill='yellow')
        for x in range(40,220,10):
            px=(x-38)*4;d.line((px,row*224+12,px,(row+1)*224),fill='#63889a');d.text((px,row*224+12),str(x),fill='yellow')
        for y in range(100,156,5):
            py=row*224+(y-100)*4;d.line((0,py,720,py),fill='#63889a');d.text((4,py),str(y),fill='yellow')
        old=Image.open(p/'source/shake-head-solid/key_-30.png').crop((38,100,218,156)).resize((720,224),Image.Resampling.NEAREST)
        board.paste(old,(720,row*224),old);d.text((724,row*224),'registered -30 neck/hair',fill='yellow')
    board.save(ROOT/f'validation/head-turn-joints/grid-{page+1}.png')
