package Demo;

public abstract class Builder {
	protected String name;
	protected Computer computer;
	
	public String getname(){
		return name;
	}
	public void setname(String str){
		name=str;
	}
	
	public Computer getcomputer(){
		return computer;
	}
	public void setcomputer(Computer com){
		computer=com;
	}
	
	public Builder(){
		computer=new Computer();		
	}
	
	public abstract void setupMainBoard();
	public abstract void setupCPU();
	public abstract void setupHardDisk();
	public abstract void setupMemory();
	public abstract void setupVideoCard();

}
